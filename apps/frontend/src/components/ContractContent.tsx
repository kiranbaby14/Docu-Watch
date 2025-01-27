import React from 'react';
import { AlertTriangle, Calendar, Users, Scale, FileText } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import type { Contract } from '@/types/contracts';

interface ContractContentProps {
  contract: Contract;
}

const getRiskBadgeColor = (level: string) => {
  switch (level.toUpperCase()) {
    case 'HIGH':
      return 'bg-red-100 text-red-800';
    case 'MEDIUM':
      return 'bg-yellow-100 text-yellow-800';
    case 'LOW':
      return 'bg-green-100 text-green-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

const getStatusBadgeColor = (status: string) => {
  switch (status.toUpperCase()) {
    case 'PENDING':
      return 'bg-blue-100 text-blue-800';
    case 'COMPLETED':
      return 'bg-green-100 text-green-800';
    case 'OVERDUE':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

const ContractContent: React.FC<ContractContentProps> = ({ contract }) => {
  return (
    <div className="space-y-6 px-2 pt-4">
      {/* Key Details Grid */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Dates Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Key Dates
            </CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="space-y-2">
              <div>
                <dt className="text-sm text-gray-500">Effective Date</dt>
                <dd className="font-medium">
                  {new Date(
                    contract.agreement.effective_date
                  ).toLocaleDateString()}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Expiration Date</dt>
                <dd className="font-medium">
                  {new Date(
                    contract.agreement.expiration_date
                  ).toLocaleDateString()}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Renewal Term</dt>
                <dd className="font-medium">
                  {contract.agreement.renewal_term}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Notice Period</dt>
                <dd className="font-medium">
                  {contract.agreement.Notice_period_to_Terminate_Renewal}
                </dd>
              </div>
            </dl>
          </CardContent>
        </Card>

        {/* Parties Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Parties Involved
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {contract.agreement.parties.map((party, index) => (
                <div key={index} className="space-y-1">
                  <div className="font-medium">{party.role}</div>
                  <div className="text-sm text-gray-600">{party.name}</div>
                  <div className="text-xs text-gray-500">
                    {party.incorporation_state}, {party.incorporation_country}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Governing Law Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Scale className="h-5 w-5" />
              Governing Law
            </CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="space-y-2">
              <div>
                <dt className="text-sm text-gray-500">Jurisdiction</dt>
                <dd className="font-medium">
                  {contract.agreement.governing_law.state},{' '}
                  {contract.agreement.governing_law.country}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Most Favored Country</dt>
                <dd className="font-medium">
                  {contract.agreement.governing_law.most_favored_country}
                </dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      </div>

      {/* Risks Section */}
      {contract.agreement.risks && contract.agreement.risks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              Risk Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {contract.agreement.risks.map((risk, index) => (
                <Alert key={index} variant="default">
                  <AlertTitle className="flex items-center justify-between">
                    <span>{risk.risk_type}</span>
                    <span
                      className={`rounded-full px-2 py-1 text-xs font-medium ${getRiskBadgeColor(
                        risk.level
                      )}`}
                    >
                      {risk.level}
                    </span>
                  </AlertTitle>
                  <AlertDescription className="mt-2">
                    <p className="font-medium">{risk.description}</p>
                    <p className="mt-1 text-sm text-gray-600">
                      Impact: {risk.impact}
                    </p>
                    {risk.related_clause && (
                      <p className="text-sm text-gray-500">
                        Related to: {risk.related_clause}
                      </p>
                    )}
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Obligations Section */}
      {contract.agreement.obligations &&
        contract.agreement.obligations.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Obligations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {contract.agreement.obligations.map((obligation, index) => (
                  <div
                    key={index}
                    className="rounded-lg border border-gray-200 p-4"
                  >
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <p className="font-medium">{obligation.description}</p>
                        <p className="text-sm text-gray-600">
                          Due:{' '}
                          {new Date(obligation.due_date).toLocaleDateString()}
                        </p>
                        {obligation.recurring && (
                          <p className="text-sm text-gray-600">
                            Recurs: {obligation.recurrence_pattern}
                          </p>
                        )}
                        {obligation.reminder_days > 0 && (
                          <p className="text-sm text-gray-600">
                            Reminder: {obligation.reminder_days} days before due
                            date
                          </p>
                        )}
                      </div>
                      <span
                        className={`rounded-full px-2 py-1 text-xs font-medium ${getStatusBadgeColor(
                          obligation.status
                        )}`}
                      >
                        {obligation.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

      {/* Industry Patterns */}
      <Card>
        <CardHeader>
          <CardTitle>Industry Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h4 className="font-medium">Industry</h4>
              <p className="text-gray-600">
                {contract.agreement.industry_patterns.industry}
              </p>
            </div>
            {contract.agreement.industry_patterns.unusual_clauses.length >
              0 && (
              <div>
                <h4 className="font-medium">Unusual Clauses</h4>
                <ul className="list-inside list-disc text-gray-600">
                  {contract.agreement.industry_patterns.unusual_clauses.map(
                    (clause, index) => (
                      <li key={index}>{clause}</li>
                    )
                  )}
                </ul>
              </div>
            )}
            <div>
              <h4 className="font-medium">Common Patterns</h4>
              <ul className="list-inside list-disc text-gray-600">
                {contract.agreement.industry_patterns.common_patterns.map(
                  (pattern, index) => (
                    <li key={index}>{pattern}</li>
                  )
                )}
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export { ContractContent };
